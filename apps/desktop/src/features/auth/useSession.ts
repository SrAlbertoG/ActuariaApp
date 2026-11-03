import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {ApiError} from "../../lib/api";
import { authApi } from "./authApi";
import type {LoginPayload,SessionStatus,WindowsInfo} from "./types";


export interface SessionState{
    status : SessionStatus;
    autoLoginError : {code : string; message : string} | null;
}

const SESSION_KEY = ["session"];

async function bootstrap(): Promise<SessionState> {
    try{
        return {status : await authApi.autoLogin(), autoLoginError: null};
    }catch(e) {
        if (!(e instanceof ApiError) || e.code === "backend_unreachable") throw e;
        const status = await authApi.status();
        return {status, autoLoginError: { code : e.code, message : e.message}};
    }
}

export function useSession(){
    return useQuery<SessionState, Error>({
        queryKey : SESSION_KEY,
        queryFn : bootstrap,
        retry : false,
        staleTime : Infinity,
        refetchOnWindowFocus : false,
    });
}

function useSetSession(){
    const queryClient = useQueryClient();
    return (status : SessionStatus) =>
        queryClient.setQueryData<SessionState>(SESSION_KEY, {status, autoLoginError: null});
}

export function useLogin(){
    const setSession = useSetSession();
    return useMutation<SessionStatus, ApiError, {payload: LoginPayload; remember: boolean}>({
        mutationFn : async({payload, remember}) => {
            let status = await authApi.login(payload);
            if (remember) status = await authApi.remember();
            return status;
        },
        onSuccess : setSession,
    });
}

export function useLogout(){
    const setSession = useSetSession();
    return useMutation<SessionStatus, ApiError>({
        mutationFn : authApi.logout,
        onSuccess : setSession,
    });
}

export function useForgetCredentials(){
    const setSession = useSetSession();
    return useMutation<SessionStatus, ApiError>({
        mutationFn : authApi.forgetCredentials,
        onSuccess : setSession,
    });
}

export function useWindowsInfo(enabled : boolean){

    return useQuery<WindowsInfo, Error>({
        queryKey: ["windows-info"],
        queryFn: authApi.windowsInfo,
        enabled,
        staleTime: Infinity,
        retry: false,
    });
}