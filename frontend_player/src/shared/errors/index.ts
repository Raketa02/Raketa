export {
  AppError,
  isAppError,
  networkUnavailable,
  timedOut,
  unknownFailure,
  type AppErrorContext,
  type AppErrorKind,
  type Recovery,
} from './AppError';
export {
  mapDecodeFailure,
  mapErrorResponse,
  mapTransportFailure,
  type ErrorEnvelope,
} from './mapError';
