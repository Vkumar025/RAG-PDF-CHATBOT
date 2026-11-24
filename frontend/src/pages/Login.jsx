import { useState } from "react";

import toast from "react-hot-toast";

import {
  loginUser
} from "../api/authApi";

function Login({
  onLoginSuccess,
  goToSignup
}) {

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      toast.error("Please enter both email and password");
      return;
    }

    if (!email.includes("@")) {
      toast.error("Please enter a valid email address (e.g. user@example.com)");
      return;
    }

    try {
      const response = await loginUser({
        email: email.trim(),
        password
      });

      localStorage.setItem("token", response.data.token);
      toast.success("Login Successful");
      onLoginSuccess(response.data.token);
    } catch (error) {
      const detail = error.response?.data?.detail;
      const errorMsg = Array.isArray(detail)
        ? detail.map((d) => d.msg).join(", ")
        : typeof detail === "string"
        ? detail
        : "Login Failed";
      toast.error(errorMsg);
    }
  };

  return (

    <div className="auth-page">

      <div className="auth-card">

        <h1>
          Welcome Back
        </h1>

        <p>
          Login to continue using
          AI PDF Chatbot
        </p>

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
          onClick={handleLogin}
        >
          Login
        </button>

        <span>

          Don't have an account?

          <strong
            onClick={goToSignup}
          >
            Sign Up
          </strong>

        </span>

      </div>

    </div>
  );
}

export default Login;