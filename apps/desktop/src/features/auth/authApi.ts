import { apiFetch } from "../../lib/api";

import type { LoginPayload, SessionStatus, WindowsInfo } from "./types";

const BASE = "/auth/sql-server";

export const authApi = {
    status : () => apiFetch<SessionStatus>(`${BASE}/status`),

    login: (payload : LoginPayload) =>
        apiFetch<SessionStatus>(`${BASE}/login`, {
            method: "POST",
            body: JSON.stringify(payload),
        }),

    autoLogin: () => apiFetch<SessionStatus>(`${BASE}/auto-login`,{method : "POST"}),

    remember: () => apiFetch<SessionStatus>(`${BASE}/remember`,{method : "POST"}),

    forgetCredentials: () =>
        apiFetch<SessionStatus>(`${BASE}/credentials`,{method : "DELETE"}),

    logout : () => apiFetch<SessionStatus>(`${BASE}/logout`,{method : "POST"}),

    windowsInfo : () => apiFetch<WindowsInfo>(`${BASE}/windows-info`),
    

};