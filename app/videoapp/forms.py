from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField
from wtforms.validators import  DataRequired


class AddTorrentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    file = FileField('File', validators=[DataRequired()])
    submit = SubmitField('Upload')
