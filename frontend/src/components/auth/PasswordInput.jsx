import { useState } from "react";
import { Eye, EyeOff, Lock } from "lucide-react";
import FormField from "./FormField.jsx";

export default function PasswordInput(props) {
  const [show, setShow] = useState(false);
  return (
    <FormField
      {...props}
      icon={Lock}
      type={show ? "text" : "password"}
      right={
        <button type="button" onClick={() => setShow((s) => !s)} aria-label={show ? "Hide password" : "Show password"} className="rounded-lg p-1.5 text-slate-500 transition hover:text-slate-200">
          {show ? <EyeOff size={17} /> : <Eye size={17} />}
        </button>
      }
    />
  );
}
