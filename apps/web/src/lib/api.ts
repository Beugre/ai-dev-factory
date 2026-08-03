const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000';
const API = `${BASE_URL}/api/v1`;

export class ApiError extends Error {
    constructor(
        public code: string,
        message: string,
        public status: number,
    ) {
        super(message);
    }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${API}${path}`, {
        ...init,
        headers: {
            'Content-Type': 'application/json',
            ...(init?.headers ?? {}),
        },
    });
    if (!response.ok) {
        let code = 'error';
        let message = response.statusText;
        try {
            const body = (await response.json()) as { code?: string; message?: string };
            code = body.code ?? code;
            message = body.message ?? message;
        } catch {
            // non-JSON error body
        }
        throw new ApiError(code, message, response.status);
    }
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
}

export const api = {
    get: <T>(path: string) => request<T>(path),
    post: <T>(path: string, body?: unknown) =>
        request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
};

export { BASE_URL };
