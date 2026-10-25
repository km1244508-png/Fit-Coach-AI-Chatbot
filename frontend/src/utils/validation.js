// Client-side validation mirrors the server rules (app/schemas/auth.py).
export const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
export const PASSWORD_HINT = "8-64 characters with at least one letter and one number.";

export function validateLogin({ email, password }) {
  const errors = {};
  if (!email.trim()) errors.email = "Email is required.";
  else if (!EMAIL_RE.test(email.trim())) errors.email = "Enter a valid email address.";
  if (!password) errors.password = "Password is required.";
  return errors;
}

export function validateRegister({ name, email, password, confirm_password }) {
  const errors = {};
  const cleanName = name.trim().replace(/\s+/g, " ");
  if (cleanName.length < 2) errors.name = "Name must be at least 2 characters.";
  else if (cleanName.length > 60) errors.name = "Name must be 60 characters or fewer.";
  if (!email.trim()) errors.email = "Email is required.";
  else if (!EMAIL_RE.test(email.trim())) errors.email = "Enter a valid email address.";
  if (password.length < 8 || password.length > 64 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) {
    errors.password = `Password must be ${PASSWORD_HINT}`;
  }
  if (!confirm_password) errors.confirm_password = "Please confirm your password.";
  else if (confirm_password !== password) errors.confirm_password = "Passwords do not match.";
  return errors;
}

export function passwordStrength(pw) {
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Za-z]/.test(pw) && /\d/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw) || (/[a-z]/.test(pw) && /[A-Z]/.test(pw))) score++;
  return Math.min(score, 4); // 0..4
}
