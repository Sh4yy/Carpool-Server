from flask import Flask
from Carpool import mod


def main():

    app = Flask(__name__)
    app.register_blueprint(mod)

    app.run(host="0.0.0.0", port=8080, debug=True)


if __name__ == '__main__':
    main()
