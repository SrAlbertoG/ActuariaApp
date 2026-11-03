import {config} from "./config";

export class ApiError extends Error{
    readonly code : string; 
    readonly status : number;

    constructor(code:string, message: string, status: number){
        super(message);
        this.name = "ApiError";
        this.code = code;
        this.status = status;
    }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
    let response : Response;

    try{
        response = await fetch(`${config.apiUrl}/api/v1${path}`,{
            ...init,
            headers: {
                "Content-Type": "application/json",
                "X-Session-Token" : config.apiToken,
                ...init.headers,
            },
        });
    } catch {
        throw new ApiError(
            "backend_unreachable",
            "No se pudo conectar al servicio local de la aplicacion",
            0,
        );
    }

    if (!response.ok){
        let code = "unexpected_error";
        let message = "Ocurrio un error inesperado";

        try{
            const body = await response.json();
            if(body?.error) {
                code = body.error.code;
                message = body.error.message;
            }else if(response.status === 422) {
                code = "Validation_error";
                message = "Revisa los datos ingresados.";
            }
        }catch {

        }
        throw new ApiError(code, message, response.status);
    }

    return (await response.json() as T);
}