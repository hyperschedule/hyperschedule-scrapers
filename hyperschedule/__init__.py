"""
Utility library for Hyperschedule scrapers. Contains the
maintainer-facing API for writing a scraper.
"""

import abc
import datetime

import dateparser


class Log:
    """
    Class handling logging. Used both by the Hyperschedule library and
    by scrapers.
    """

    def _log(self, level, msg, *args, **kwargs):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        msg_str = msg.format(*args, **kwargs)
        print("{} [{}] {}".format(timestamp, level.upper(), msg_str))

    def info(self, msg, *args, **kwargs):
        self._log("info", msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self._log("warn", msg, *args, **kwargs)


# Global logging object.
log = Log()


class MaintainerError(Exception):
    """
    Exception raised when the maintainer misuses the Hyperschedule
    library.
    """

    def __init__(self, msg, *args, **kwargs):
        """
        Construct a new `MaintainerError`, passing the `msg`, `args`, and
        `kwargs` to `str.format`.
        """
        super().__init__(msg.format(*args, **kwargs))


class Date:
    """
    Class representing a specific day of the year. Immutable.
    """

    def __init__(self, string):
        """
        Construct a date from the given `string`, trying very hard to make
        something sensible out of whatever you provide. Suggested
        format is YYYY-MM-DD, but anything might work.
        """
        try:
            dt = dateparser.parse(string)
            if dt is None:
                raise ValueError
        except ValueError:
            raise MaintainerError("Date got invalid string: {}", string) from None
        self.year = dt.year
        self.month = dt.month
        self.day = dt.day

    def __str__(self):
        return "{}-{}-{}".format(self.year, self.month, self.day)


class Time:
    """
    Class representing a specific time of day. Immutable.
    """

    def __init__(self, string):
        """
        Construct a time from the given `string`, trying very hard to make
        something sensible out of whatever you provide. Suggested
        format is HH:MM, but anything might work.
        """
        try:
            dt = dateparser.parse(string)
            if dt is None:
                raise ValueError
        except ValueError:
            raise MaintainerError("Time got invalid string: {}", string) from None
        self.hour = dt.hour
        self.minute = dt.minute

    def __str__(self):
        hour = (self.hour - 1) % 12 + 1
        minute = self.minute
        ampm = "AM" if self.hour < 12 else "PM"
        return "{}:{} {}".format(hour, minute, ampm)


class Weekdays:
    """
    Class representing some subset of the days of the week (Monday
    through Sunday).
    """

    CHARS = "MTWRFSU"

    def __init__(self, days=None):
        """
        Construct a new set of `Weekdays`. By default it is empty. If you
        pass `days`, it should be an iterable containing days to add
        to the `Weekdays`, for example "MWF".
        """
        self.days = set()
        if days is not None:
            for day in days:
                self.add_day(day)

    def add_day(self, day):
        """
        Add a day (a character from the string "MTWRFSU") to the set of
        `Weekdays`.
        """
        day = day.upper()
        if day not in Weekdays.CHARS:
            raise MaintainerError("add_day got invalid day: {}", day)
        if day in days:
            log.warn("add_day got same day more than once: {}", day)
        days.add(day)

    def is_empty(self):
        """
        Check if there are no days in this `Weekdays` object.
        """
        return bool(self.days)

    def __str__(self):
        return "".join(sorted(self.days, key=lambda d: Weekdays.CHARS.index(d)))


class Subterm:
    """
    Class representing either the entirety of a term or only a
    sub-part, in the abstract. Immutable. This class represents
    "full-term", "first half-term", "second half-term", and so on,
    without making reference to any specific term. For those simple
    cases, consider using the constants `FullTerm`, `FirstHalfTerm`,
    `SecondHalfTerm`, and so on.
    """

    def __init__(self, *subterms):
        """
        Construct a new `Subterm` from the given arguments, booleans. The
        number of arguments is the number of parts into which the term
        is divided. If an argument is truthy, then that sub-term is
        included in this `Subterm`; if an argument is falsy, then it
        is not.

        For example:

        FullTerm = Subterm(True)
        FirstHalfTerm = Subterm(True, False)
        SecondHalfTerm = Subterm(False, True)
        """
        if not subterms:
            raise MaintainerError("Subterm got no arguments")
        if not any(subterms):
            raise MaintainerError("Subterm got no truthy arguments: {}", subterms)
        self.subterms = tuple(map(bool, subterms))

    def __str__(self):
        fractions = [
            "{}/{}".format(idx + 1, len(self.subterms))
            for idx, included in enumerate(self.subterms)
            if included
        ]
        return ", ".join(fractions)


# Indicates that a course runs for the entire term.
FullTerm = Subterm(True)

# Indicates that a course runs for only the first half of the term.
FirstHalfTerm = Subterm(True, False)

# Indicates that a course runs for only the second half of the term.
SecondHalfTerm = Subterm(False, True)

# Indicates that a course runs for only the first third of the term.
FirstThirdTerm = Subterm(True, False, False)

# Indicates that a course runs for only the middle third of the term.
MiddleThirdTerm = Subterm(False, True, False)

# Indicates that a course runs for only the last third of the term.
LastThirdTerm = Subterm(False, False, True)

# Indicates that a course runs for the first two-thirds of the term.
FirstAndMiddleThirdTerms = Subterm(True, True, False)

# Indicates that a course runs for the last two-thirds of the term.
MiddleAndLastThirdTerms = Subterm(False, True, True)


class Meeting:
    """
    Class representing a single recurring meeting time for a course.
    """

    def __init__(
        self,
        start_date=None,
        end_date=None,
        weekdays=None,
        start_time=None,
        end_time=None,
        subterm=None,
        location=None,
    ):
        self.start_date = None
        self.end_date = None
        self.weekdays = None
        self.start_time = None
        self.end_time = None
        self.subterm = None
        self.location = None
        if start_date is not None:
            self.set_start_date(start_date)
        if end_date is not None:
            self.set_end_date(end_date)
        if weekdays is not None:
            self.set_weekdays(weekdays)
        if start_time is not None:
            self.set_start_time(start_time)
        if end_time is not None:
            self.set_end_time(end_time)
        if subterm is not None:
            self.set_subterm(subterm)
        if location is not None:
            self.set_location(location)

    def set_dates(self, start_date, end_date):
        self.set_start_date(start_date)
        self.set_end_date(end_date)

    def set_times(self, start_time, end_time):
        self.set_start_time(start_time)
        self.set_end_time(end_time)

    def set_start_date(self, start_date):
        if not isinstance(start_date, Date):
            raise MaintainerError("set_start_date got non-Date: {}", start_date)
        self.start_date = start_date
        self._check_dates()

    def set_end_date(self, end_date):
        if not isinstance(end_date, Date):
            raise MaintainerError("set_end_date got non-Date: {}", end_date)
        self.end_date = end_date
        self._check_dates()

    def set_weekdays(self, weekdays):
        if not isinstance(weekdays, Weekdays):
            raise MaintainerError("set_weekdays got non-Weekdays: {}", weekdays)
        if weekdays.is_empty():
            raise MaintainerError("set_weekdays got empty Weekdays")
        self.weekdays = weekdays

    def set_start_time(self, start_time):
        if not isinstance(start_time, Time):
            raise MaintainerError("set_start_time got non-Time: {}", start_time)
        self.start_time = start_time
        self._check_times()

    def set_end_time(self, end_time):
        if not isinstance(end_time, Time):
            raise MaintainerError("set_end_time got non-Time: {}", end_time)
        self.end_time = end_time
        self._check_times()

    def set_subterm(self, subterm):
        if not isinstance(subterm, Subterm):
            raise MaintainerError("set_subterm got non-Subterm: {}", subterm)
        self.subterm = subterm

    def set_location(self, location):
        if not isinstance(location, Location):
            raise MaintainerError("set_location got non-string: {}", location)
        self.location = location

    def _check_dates(self):
        if self.start_date is not None and self.end_date is not None:
            if self.start_date >= self.end_date:
                raise MaintainerError(
                    "Meeting start date not before end date: {} >= {}",
                    self.start_date,
                    self.end_date,
                )

    def _check_times(self):
        if self.start_time is not None and self.end_time is not None:
            if self.start_time >= self.end_time:
                raise MaintainerError(
                    "Meeting start time not before end time: {} >= {}",
                    self.start_time,
                    self.end_time,
                )

    def _is_valid(self):
        # TODO: implement
        pass

    # TODO: write docstrings


class Schedule:
    """
    Class representing the set of all of a course's scheduled meeting
    times.
    """

    # TODO: implement


class Course:
    """
    Class representing a university course, the core abstraction of
    Hyperschedule. Each course is displayed as a separate object on
    the frontend. Courses may not have multiple sections; sections are
    instead represented by multiple `Course` objects.
    """

    def __init__(
        self,
        code=None,
        name=None,
        description=None,
        schedule=None,
        instructors=None,
        num_credits=None,
        enrollment_status=None,
        num_seats_filled=None,
        num_seats_total=None,
        waitlist_length=None,
        sort_key=None,
        mutual_exclusion_key=None,
    ):
        """
        TODO: write
        """

    # TODO: implement


class ScraperResult:
    """
    Class representing the result of running a scraper. Conceptually,
    it contains two things: a set of `Course` objects, and a `Term`
    object.
    """

    def __init__(self, term=None, courses=None):
        self.term = None
        self.courses = {}
        if term is not None:
            self.set_term(term)
        if courses is not None:
            for course in courses:
                self.add_course(course)

    def add_course(self, course):
        if not isinstance(course, Course):
            raise MaintainerError("add_course got non-course: {}", course)
        code = course.get_code()
        if code in self.courses:
            log.warn("multiple courses with same code: {}", code)
        self.courses[code] = course

    def set_term(self, term):
        if not isinstance(term, Term):
            raise MaintainerError("set_term got non-term: {}", term)
        self.term = term


class Scraper(abc.ABC):
    """
    Class representing a Hyperschedule scraper. Subclass this to
    create a scraper for a new school.
    """

    def __init__(self, **kwargs):
        """
        Construct a new instance of the scraper. The keyword arguments
        `kwargs` come from the `options` key of the configuration file
        "scrapers.json" in the root of this repository.
        """

    @abc.abstractmethod
    def run(self):
        """
        Retrieve basic course data from the university's course database,
        and return it as a `ScraperResult` object.

        This method should not take longer than 15 minutes to run. If
        it takes too long, consider fetching only basic information
        about each course and then implementing the optional `refine`
        method to fill in the rest of the information for each course
        later.
        """

    def refine(self, course):
        """
        Fetch additional information about a course from the university's
        course database. The `course` argument is a `Course` object,
        and the return value should be another `Course` object. You
        may mutate `course` directly if you wish, and may return None
        as a shorthand for returning the original `Course` object.

        This method is optional. It is useful when it is possible to
        fetch basic information about all the courses initially, but
        filling in the rest of the details requires fetching
        information individually for each course. If you implement
        this method, then Hyperschedule will handle calling it
        automatically in parallel and stopping before the 15-minute
        timeout, and then resuming where it left off the next time the
        scraper is called.
        """
