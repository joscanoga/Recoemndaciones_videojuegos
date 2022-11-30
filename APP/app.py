from flask import Flask, render_template, request
from recommendation_module import recommendation as rec
import pandas as pd

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
    juegos = ["pelicula 1", "pelicula 23", "pelicula 3"]
    matrix=rec.matrix

    if request.method == "GET":
        juegos = pd.DataFrame(rec.header).sample(10).values

        return render_template("recomendacion.html",juegos=juegos)
    else:

        recomendados=rec.recommend_games(matrix,rec.build_user_vector(request.form.to_dict(),rec.header),rec.header,5)
        print(recomendados)
        return render_template("lista.html",juegos=recomendados)


@app.route('/resultados')
def resultaos():  # put application's code here
    return render_template("recomendacion.html")
if __name__ == '__main__':
    app.run()
