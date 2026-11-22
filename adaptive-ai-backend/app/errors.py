class SessionAccessError(Exception):
    """The session belongs to a different user."""


class FeedbackExistsError(Exception):
    """Feedback was already stored for this interaction."""
