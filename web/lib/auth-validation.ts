export type LoginFieldErrors = {
  email?: string;
  password?: string;
};

export type SignupFieldErrors = {
  email?: string;
};

export type SignupVerifyFieldErrors = {
  password?: string;
  confirmPassword?: string;
};

export type ForgotPasswordFieldErrors = {
  email?: string;
};

export type ResetPasswordFieldErrors = {
  newPassword?: string;
  confirmPassword?: string;
};

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
export const PASSWORD_MIN_LENGTH = 10;
export const PASSWORD_MAX_LENGTH = 128;

export function validateLoginFields(email: string, password: string): LoginFieldErrors {
  const errors: LoginFieldErrors = {};

  if (!email.trim()) {
    errors.email = "Email is required.";
  } else if (!EMAIL_PATTERN.test(email.trim())) {
    errors.email = "Enter a valid email address.";
  }

  if (!password.trim()) {
    errors.password = "Password is required.";
  }

  return errors;
}

export function validateSignupEmail(email: string): SignupFieldErrors {
  const errors: SignupFieldErrors = {};
  if (!email.trim()) {
    errors.email = "Email is required.";
  } else if (!EMAIL_PATTERN.test(email.trim())) {
    errors.email = "Enter a valid email address.";
  }
  return errors;
}

export function validateSignupPasswords(
  password: string,
  confirmPassword: string,
): SignupVerifyFieldErrors {
  const errors: SignupVerifyFieldErrors = {};
  const trimmedPassword = password.trim();
  const trimmedConfirm = confirmPassword.trim();

  if (!trimmedPassword) {
    errors.password = "Password is required.";
  } else if (trimmedPassword.length < PASSWORD_MIN_LENGTH) {
    errors.password = `Password must be at least ${PASSWORD_MIN_LENGTH} characters.`;
  } else if (trimmedPassword.length > PASSWORD_MAX_LENGTH) {
    errors.password = `Password must be at most ${PASSWORD_MAX_LENGTH} characters.`;
  }

  if (!trimmedConfirm) {
    errors.confirmPassword = "Confirm password is required.";
  } else if (trimmedPassword !== trimmedConfirm) {
    errors.confirmPassword = "Passwords do not match.";
  }

  return errors;
}

export function validateForgotPasswordEmail(email: string): ForgotPasswordFieldErrors {
  const errors: ForgotPasswordFieldErrors = {};

  if (!email.trim()) {
    errors.email = "Email is required.";
  } else if (!EMAIL_PATTERN.test(email.trim())) {
    errors.email = "Enter a valid email address.";
  }

  return errors;
}

export function validateResetPasswords(
  newPassword: string,
  confirmPassword: string,
): ResetPasswordFieldErrors {
  const errors: ResetPasswordFieldErrors = {};
  const trimmedPassword = newPassword.trim();
  const trimmedConfirm = confirmPassword.trim();

  if (!trimmedPassword) {
    errors.newPassword = "New password is required.";
  } else if (trimmedPassword.length < PASSWORD_MIN_LENGTH) {
    errors.newPassword = `Password must be at least ${PASSWORD_MIN_LENGTH} characters.`;
  } else if (trimmedPassword.length > PASSWORD_MAX_LENGTH) {
    errors.newPassword = `Password must be at most ${PASSWORD_MAX_LENGTH} characters.`;
  }

  if (!trimmedConfirm) {
    errors.confirmPassword = "Confirm password is required.";
  } else if (trimmedPassword !== trimmedConfirm) {
    errors.confirmPassword = "Passwords do not match.";
  }

  return errors;
}
