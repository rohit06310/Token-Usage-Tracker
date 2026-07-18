const BASE = "/api/proxy";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = `HTTP ${response.status}`;

    try {
      const body = await response.json();
      message =
        body.detail ??
        body.message ??
        message;
    } catch {}

    throw new ApiError(
      response.status,
      message
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export async function login(
  email: string,
  password: string
): Promise<void> {
  const response = await fetch(
    "/api/auth/login",
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify({
        email,
        password,
      }),
    }
  );

  if (!response.ok) {
    const body =
      await response
        .json()
        .catch(() => ({}));

    throw new ApiError(
      response.status,
      body.message ??
        "Login failed."
    );
  }
}

export async function logout() {
  await fetch("/api/auth/logout", {
    method: "POST",
  });
}

export async function swrFetcher<T>(
  url: string
): Promise<T> {
  const response = await fetch(url);

  if (!response.ok) {
    throw new ApiError(
      response.status,
      response.statusText
    );
  }

  return response.json();
}

export const api = {
  get: <T>(path: string) =>
    request<T>(path),

  post: <T>(
    path: string,
    body?: unknown
  ) =>
    request<T>(path, {
      method: "POST",
      body: body
        ? JSON.stringify(body)
        : undefined,
    }),

  put: <T>(
    path: string,
    body?: unknown
  ) =>
    request<T>(path, {
      method: "PUT",
      body: body
        ? JSON.stringify(body)
        : undefined,
    }),

  patch: <T>(
    path: string,
    body?: unknown
  ) =>
    request<T>(path, {
      method: "PATCH",
      body: body
        ? JSON.stringify(body)
        : undefined,
    }),

  delete: <T>(path: string) =>
    request<T>(path, {
      method: "DELETE",
    }),
};