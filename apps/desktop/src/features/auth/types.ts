export type AuthType = "sql" | "windows";

export interface SavedProfile{
    server : string;
    database : string | null;
    auth_type : AuthType;
    username : string | null;
}

export interface SessionStatus{
    connected : boolean;
    server : string | null;
    database : string | null;
    username : string | null;
    auth_type : AuthType | null;
    has_saved_credentials : boolean;
    saved_profile : SavedProfile | null;
}

export interface LoginPayload{
    server : string;
    database : string | null;
    auth_type : AuthType;
    username : string | null;
    password : string | null;
}

export interface WindowsInfo{
    available : boolean;
    account : string | null;
    domain_joined : boolean;
    message: string | null;
}

