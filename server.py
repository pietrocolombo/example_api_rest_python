from flask import Flask, render_template
from flask_restful import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy
import json
import time
import logging

REFRESH_PAGE = 5

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

logging.basicConfig(level=logging.INFO, filename='server_log.log')


class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Boolean, nullable=False)
    config = db.Column(db.Integer, nullable=False)
    data = db.relationship('Data', backref='device', lazy=True, cascade="all, delete-orphan")


class Data(db.Model):
    id_device = db.Column(db.Integer, db.ForeignKey('device.id'), primary_key=True)
    timestamp = db.Column(db.Float, primary_key=True)
    data = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"Data(id_device = {self.id_device}, timestamp = {self.timestamp}, data = {self.data})"


device_data_put_args = reqparse.RequestParser()
device_data_put_args.add_argument("id_device", type=int, help="id device", required=True)
device_data_put_args.add_argument("timestamp", type=float, help="timestamp epoc", required=True)
device_data_put_args.add_argument("data", type=float, help="data", required=True)

device_data_delete_args = reqparse.RequestParser()
device_data_delete_args.add_argument("id_device", type=int, help="id device", required=True)
device_data_delete_args.add_argument("timestamp", type=float, help="timestamp epoc", required=True)


class DataDevice(Resource):
    def put(self):
        """ it receives the data from the devices and puts them in the database

        :return:
        """
        args = device_data_put_args.parse_args()
        # check if the device exist
        device = Device.query.get(args['id_device'])
        if device is None:
            # device is not in the database so we add to it
            device = Device(id=args['id_device'], status=True, config=0)

        # add data to the database
        data = Data(id_device=args['id_device'], timestamp=args['timestamp'], data=args['data'])
        device.data.append(data)
        device.status = True
        db.session.add(device)
        db.session.add(data)
        db.session.commit()

        response = app.response_class(
            response=json.dumps(device.config),
            status=201,
            mimetype='application/json')

        return response

    def delete(self):
        """ delete a row from Data Table

        :return:
        """
        args = device_data_delete_args.parse_args()
        n_delete = Data.query.filter(Data.id_device == args['id_device'], Data.timestamp == args['timestamp']).delete()
        db.session.commit()
        after_n_delete = Data.query.filter(Data.id_device == args['id_device']).all()
        if not after_n_delete:
            Device.query.filter(Device.id == args['id_device']).delete()
            db.session.commit()
        if n_delete >= 1:
            return '', 204
        else:
            return '', 404


api.add_resource(DataDevice, "/data_device")

@app.route("/")
def home():
    """ Home page for data visualization

    :return:
    """
    devices_id = []
    seconds = time.time() - REFRESH_PAGE
    devices = Device.query.all()
    all_data = []
    for device in devices:
        data = Data.query.with_entities(Data.data).filter(Data.id_device == device.id,
                                                          Data.timestamp >= seconds).all()
        if data:
            data = {'id_device': device.id, 'config': device.config, 'status': device.status,
                    'data': [item for sublist in data for item in sublist]}
        else:
            data = {'id_device': device.id, 'config': device.config, 'status': device.status,
                    'data': []}
        all_data.append(data)

    return render_template("index.html", all_data=all_data, refresh=REFRESH_PAGE)


if __name__ == '__main__':
    db.create_all()
    app.run(host='localhost', port=5000)