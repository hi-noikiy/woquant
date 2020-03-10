from flask import Flask

app = Flask(
    __name__,
    static_folder='output'
)

app.run(host="0.0.0.0" , port=9999)
