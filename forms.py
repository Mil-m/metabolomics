from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional


class MetabolightsStudyInfo(FlaskForm):
    study = SelectField('Study',
                        validators=[DataRequired()],
                        choices=[],
                        render_kw={'rows': 1, 'cols': 5})
    submit = SubmitField('Get study info')
