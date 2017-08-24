import datetime as dt
import wtforms
import pytz

class ListField(wtforms.Field):
    """Take a string of comma separated values, parse it to a list."""

    widget = wtforms.widgets.TextInput()

    def _value(self):
        return u",".join(self.data) if self.data else u""

    def process_formdata(self, data):
        self._data = data[0] if data else u""
        self.data = [d.strip() for d in data[0].strip(",").split(",")] if data else []


class FlexibleDateTimeField(wtforms.Field):
    """Take a string of several datatime formats and parse it to datetime object"""

    widget = wtforms.widgets.TextInput()

    def _value(self):
        return self.data.strftime("%Y-%m-%dT%H:%M:%S.%f") if self.data else ""

    def process_formdata(self, data):
        if not data:
            return u""
        allowed_fmts = ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]
        for fmt in allowed_fmts:
            try:
                self.data = dt.datetime.strptime(data[0], fmt)
                self._data = data[0] if data else u""
                return
            except ValueError:
                pass
        raise wtforms.ValidationError("{} is invalid".format(data))


class LogsQueryForm(wtforms.Form):
    """Form for Logs API query parameters."""

    # naive.. but would be okay.
    TOKEN_FMT   = "%Y%m%d%H%M%S%f"

    start       = FlexibleDateTimeField()
    end         = FlexibleDateTimeField()
    freq        = wtforms.StringField()
    fields      = ListField()
    order       = wtforms.IntegerField()
    token       = wtforms.StringField()
    func        = wtforms.StringField()

    def validate_start(self, field):
        if not field.data:
            self.validate_end(field)
            field.data -= dt.timedelta(days=2)
        field.data = field.data.replace(tzinfo=pytz.UTC)

    def validate_end(self, field):
        if not field.data:
            field.data = dt.datetime.utcnow()
            field.data = field.data.replace(hour=0, minute=0, second=0, microsecond=0)
        field.data = field.data.replace(tzinfo=pytz.UTC)

    def validate_freq(self, field):
        if not field.data:
            field.data = "hours"
        if field.data not in ["years", "months", "days", "hours", "minutes"]:
            raise wtforms.ValidationError("{} is invalid".format(field.data))

    def validate_order(self, field):
        if not field.data:
            field.data = 1
        if field.data not in (-1, 1):
            raise wtforms.ValidationError("order 1 or ascending, -1 for descending")

    def validate_token(self, field):
        if field.data:
            try:
                field.data = dt.datetime.strptime(field.data, self.TOKEN_FMT)
                field.data = field.data.replace(tzinfo=pytz.UTC)
            except ValueError:
                raise wtforms.ValidationError("token {} is invalid".format(field.data))

    def validate_func(self, field):
        allowed_funcs = ["avg", "sum", "max", "min"]
        if not field.data:
            field.data = "avg"
        if field.data not in allowed_funcs:
            message = "func {} is invalid. Allowed: {}".format(field.data, allowed_funcs)
            raise wtforms.ValidationError(message)


class AbnormalitiesV1QueryForm(wtforms.Form):
    """Form for Abnormalities v1 API query parameters."""

    # naive.. but would be okay.
    TOKEN_FMT   = "%Y%m%d%H%M%S%f"

    start       = FlexibleDateTimeField()
    end         = FlexibleDateTimeField()
    freq        = wtforms.StringField()
    field       = wtforms.StringField()
    
    def validate_start(self, field):
        if not field.data:
            self.validate_end(field)
            field.data -= dt.timedelta(days=2)
        field.data = field.data.replace(tzinfo=pytz.UTC)

    def validate_end(self, field):
        if not field.data:
            field.data = dt.datetime.utcnow()
            field.data = field.data.replace(hour=0, minute=0, second=0, microsecond=0)
        field.data = field.data.replace(tzinfo=pytz.UTC)

    def validate_freq(self, field):
        if not field.data:
            field.data = "hours"
        if field.data not in ["years", "months", "days", "hours", "minutes"]:
            raise wtforms.ValidationError("{} is invalid".format(field.data))


class ForecastV1QueryForm(AbnormalitiesV1QueryForm):
    """Form for Forecast v1 API query parameters."""
    
    def validate_field(self, field):
        if not field.data:
            raise wtforms.ValidationError("field is empty")
        supported = ["cwshdr"]
        if field.data.lower() not in supported:
            template = "{} is not supported. Currently supported: {}"
            raise wtforms.ValidationError(template.format(field.data, supported))
