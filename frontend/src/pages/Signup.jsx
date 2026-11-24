import { useState } from "react";

import toast from "react-hot-toast";

import {
  signupUser
} from "../api/authApi";

function Signup({
  goToLogin
}) {

  const [name, setName] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const handleSignup = async () => {
    if (!name.trim() || !email.trim() || !password.trim()) {
      toast.error("Please fill in all fields");
      return;
    }

    if (!email.includes("@")) {
      toast.error("Please enter a valid email address (e.g. user@example.com)");
      return;
    }

    try {
      await signupUser({
        name: name.trim(),
        email: email.trim(),
        password
      });

      toast.success("Account Created Successfully");
      goToLogin();
    } catch (error) {
      const detail = error.response?.data?.detail;
      const errorMsg = Array.isArray(detail)
        ? detail.map((d) => d.msg).join(", ")
        : typeof detail === "string"
        ? detail
        : "Signup Failed";
      toast.error(errorMsg);
    }
  };

  return (

    <div className="auth-page">

      <div className="auth-card">

        <h1>
          Create Account
        </h1>

        <p>
          Start chatting with your
          PDFs using AI
        </p>

        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(e) =>
            setName(
              e.target.value
            )
          }
        />

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) =>
            setEmail(
              e.target.value
            )
          }
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) =>
            setPassword(
              e.target.value
            )
          }
        />

        <button
          onClick={handleSignup}
        >
          Sign Up
        </button>

        <span>

          Already have an account?

          <strong
            onClick={goToLogin}
          >
            Login
          </strong>

        </span>

      </div>

    </div>
  );
}

export default Signup;