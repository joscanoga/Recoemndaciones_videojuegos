from flask import Flask, render_template, request

app = Flask(__name__)
#variable para guardar los resultados delcliente


@app.route('/')
def inicio():  # put application's code here
    return render_template("inicio.html")

@app.route('/agregar')
def agregar():  # put application's code here
    return render_template("agregar.html")

@app.route('/recomendar',methods=["GET","POST"])
def recomendar():  # put application's code here
    if request.method == "GET":
        return render_template("recomendacion.html")
    else:
        return render_template("lista.html")


@app.route('/resultados')
def resultaos():  # put application's code here
    return render_template("recomendacion.html")
if __name__ == '__main__':
    app.run()
