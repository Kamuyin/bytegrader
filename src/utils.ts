import { URLExt } from "@jupyterlab/coreutils";
import { ServerConnection } from "@jupyterlab/services";

export interface ApiError {
  code: number;
  message: string;
  request_id?: string;
}
export class ApiErrorException extends Error {
  public code: number;
  public request_id?: string;
  constructor(err: ApiError) {
    super(err.message);
    this.name = 'ApiErrorException';
    this.code = err.code;
    this.request_id = err.request_id;
  }
}

export async function requestAPI<T>(
  endPoint = '',
  init: RequestInit = {}
): Promise<T> {
  const settings = ServerConnection.makeSettings();
  const requestUrl = URLExt.join(
    settings.baseUrl,
    endPoint
  );

  let response: Response;
  try {
    response = await ServerConnection.makeRequest(requestUrl, init, settings);
  } catch (error) {
    throw new ServerConnection.NetworkError(error as TypeError);
  }

  const data = await response.json();

  if (!response.ok) {
    const errBody = (data as any).error || { code: response.status, message: data.message || response.statusText };
    const request_id = response.headers.get('X-Request-ID') || undefined;
    throw new ApiErrorException({
      code: errBody.code,
      message: errBody.message,
      request_id
    });
  }

  return data;
}