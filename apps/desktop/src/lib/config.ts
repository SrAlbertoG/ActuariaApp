export const config = {
    apiUrl : import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8765",
    apiToken : import.meta.env.VITE_API_TOKEN ?? "",
    defaultServer : import.meta.env.VITE_DEFAULT_SERVER ?? "",
    defaultDatabase : import.meta.env.VITE_DEFAULT_DATABASE ?? "",
};