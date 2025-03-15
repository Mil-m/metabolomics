from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, Email


class MetabolightsLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class MetabolightsStudyInfo(FlaskForm):
    study = SelectField('Study',
                        validators=[DataRequired()],
                        choices=[],
                        render_kw={'rows': 1, 'cols': 5})
    submit = SubmitField('Get study info')
