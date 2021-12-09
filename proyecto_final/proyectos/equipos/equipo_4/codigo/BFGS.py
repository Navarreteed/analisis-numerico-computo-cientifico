import numpy as np
import numpy.linalg as ln
import scipy as sp
import scipy.optimize
import pandas as pd

#### Lectura de Datos

# Leer los datos, pasarlos a pandas
datos = pd.read_csv("../Datos/Stroke_Data.csv")

# Cambiamos los datos a un array de numpy pata poder trabajar con ellos. 
datos_array = np.asarray(datos)

# Tomamos la variable objetivo, en este caso, esta es `stroke`
y = datos_array[:, 0].astype('float64')

# Tomamos el resto de las variables como variables explicativas, y agregamos un
# intercepto
X = np.asarray(datos_array[:, 1:]).astype('float64')
intercept = np.ones(X.shape[0]).reshape(X.shape[0], 1)
X = np.concatenate((intercept, X), axis = 1)

#### Funciones auxiliares para la optimización

# Función de costo
def cost(beta, X=X, y=y):
    # Por simplicidad resumimos los términos
    h = np.exp(np.dot(X, beta)) 
    log_h = np.log(1.0 + h)
    
    # Regresamos la función de costo según la definimos arriba
    return np.sum(-y*np.dot(X, beta) + y*log_h + (1-y)*log_h)

# Función logit
def logit(X, beta):
    return 1/(1.0 + np.exp(-np.dot(X, beta)))

# Función de score
def score(beta, X=X, y=y):
    return np.dot(X.T, logit(X, beta) - y)

#### Implementación de BFGS

def bfgs(f, gradiente, x_init, tol=1e-6, return_all = False):
    """
    Cálculo de aproximación numérica de mínimo de una función por el método de BFGS.
    Se usa búsqueda de línea de el paquete scipy. 
    Args:
    
        f (function): función a la cual aproximar el mínimo.
        
        gradiente (function): Expresión para el gradiente de f.
        
        x_init (np.array): Punto inicial del cual seguirá el método.
        
        tol (float): Tolerancia para el problema.
        
        return_all (bool) : Si es TRUE, regresa las x_k para cada k. Si no, sólo la última.
        
    Regresa:
    
        xk (np.array): Valor final de la aproximación. 

        k (integer): Número de iteraciones. 
    """
    # Diccionario que guarda los resultados de cada iteración
    resultados = dict()
    
    # Se inicializa el número de iteraciones
    k = 0

    # Se inicializa el gradiente
    grad_k = gradiente(x_init)

    # Se calcula el tamaño necesario para la Hessiana `Hess`, dependiendo del tamaño 
    # del vector x_init. Se inicializa como la identidad. 
    n = len(x_init)
    Hess = np.eye(n)
    B_k = np.eye(n)

    # Inicialización del vector solución. 
    x_k = x_init

    # Inicializamos alfa
    alfa = 0.001

    while np.linalg.norm(grad_k,2) > tol and k < 2000:
        # pk: Aproximación a la dirección de descenso por Newton. 
        p_k = -np.dot(Hess, grad_k)

        # Busqueda de línea de scipy. Regresa varias cosas, pero solamente nos 
        # interesa el primer término, alfa. 
        alfa = sp.optimize.line_search(f, gradiente, x_k, p_k)[0]
        if alfa == None: 
            alfa = 0.01

        # Creando nueva x para siguiente iteración. 
        x_new = x_k + alfa * p_k
        
        # Calculamos `s` y `y` para la iteración k, y actualizamos x y el gradiente
        s_k = x_new - x_k
        x_k = x_new
        grad_new = gradiente(x_new)
        y_k = grad_new - grad_k
        grad_k = grad_new
        
        # Cálculo de la Aproximación con Sherman-Morrison-Woodbury
        B_k = B_k - ((B_k @ s_k) @ (s_k.transpose()  @ B_k))/(s_k.transpose() @ B_k @ s_k) + (np.outer(y_k, y_k))/(y_k.transpose() @ s_k)

        # Actualización de la aproximación a la Hessiana
        rho_k = 1.0 / (y_k.transpose() @ s_k)
        A1 = np.eye(n) - rho_k * np.outer(s_k, y_k)
        A2 = np.eye(n) - rho_k * np.outer(y_k, s_k)
        Hess = A1 @ (Hess @ A2) + (rho_k * np.outer(s_k,s_k))
        
        # Vamos guardando los valores
        resultados[k] = (x_k, k)
        
        # Subimos el número de iteraciones
        k += 1
    
    if return_all:
        return resultados
    else:
        return (x_k, k-1)    
    
    
#### Comparando scipy vs implementación

def comparar_scipy_vs_implementacion(tolerancia = 1e-5):
    
    # Optimización con BFGS a través de scipy
    sol_scipy_bfgs = sp.optimize.minimize(fun = cost,
                                          x0 = np.ones(10)*0.5, 
                                          method = 'BFGS',
                                          args = (X,y),
                                          jac = score)

    # Optimización con BFGS implementado manualmente
    result, _ = bfgs(f = cost, 
                     gradiente = score , 
                     x_init = np.ones(10)*0.5)
    
    return np.allclose(sol_scipy_bfgs.x, result, rtol = tolerancia)