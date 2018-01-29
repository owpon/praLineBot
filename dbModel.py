from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

app = Flask(__name__)
# 那個在postgresql很長的那串
postgresql_url = 'postgres://xxxxxxxxxx'

app.config['SQLALCHEMY_DATABASE_URI'] = postgresql_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)


class Add_New_Word(db.Model):
    __tablename__ = 'words'

    Id = db.Column(db.Integer, primary_key=True)
    input_word = db.Column(db.String(256))
    output_word = db.Column(db.String(256))

    def __init__(self
                 , input_word
                 , output_word
                 ):
        self.input_word = input_word
        self.output_word = output_word


class botConfig(db.Model):
    __tablename__ = 'config'

    Id = db.Column(db.Integer, primary_key=True)
    GroupId = db.Column(db.String(256))
    Item = db.Column(db.String(256))
    Status = db.Column(db.String(256))

    def __init__(self
                 , GroupId
                 , Item
                 , Status
                 ):
        self.GroupId = GroupId
        self.Item = Item
        self.Status = Status


if __name__ == '__main__':
    manager.run()
