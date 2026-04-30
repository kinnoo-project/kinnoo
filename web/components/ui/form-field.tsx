"use client";

import type { ChangeEventHandler, ReactNode } from "react";

type FormFieldProps = {
  id: string;
  name: string;
  label: string;
  type?: "text" | "email" | "password";
  value: string;
  onChange: ChangeEventHandler<HTMLInputElement>;
  placeholder?: string;
  autoComplete?: string;
  error?: string;
  helperText?: ReactNode;
};

export default function FormField({
  id,
  name,
  label,
  type = "text",
  value,
  onChange,
  placeholder,
  autoComplete,
  error,
  helperText,
}: FormFieldProps) {
  const describedBy = error ? `${id}-error` : helperText ? `${id}-help` : undefined;

  return (
    <div className="space-y-2">
      <label htmlFor={id} className="block text-sm font-medium text-white/85">
        {label}
      </label>
      <input
        id={id}
        name={name}
        type={type}
        autoComplete={autoComplete}
        className="w-full rounded-button border border-white/20 bg-black/40 px-3 py-2 text-sm text-kinnoo-text placeholder:text-white/45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        aria-invalid={Boolean(error)}
        aria-describedby={describedBy}
      />
      {helperText && !error ? (
        <p id={`${id}-help`} className="text-xs text-white/60">
          {helperText}
        </p>
      ) : null}
      {error ? (
        <p id={`${id}-error`} role="alert" className="text-sm text-red-300">
          {error}
        </p>
      ) : null}
    </div>
  );
}