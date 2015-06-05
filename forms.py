from wtforms import (Form, BooleanField, StringField,
                     PasswordField, DecimalField, validators,
                     FileField)


class CreateItemForm(Form):
    item_name = StringField('Item Name', [validators.required()])
    price = DecimalField('Price', [validators.required()])
    image = FileField('Image')
    description = StringField('Description')
