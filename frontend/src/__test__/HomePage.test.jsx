import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import HomePage from "../Pages/HomePage";

const mockedNavigate = vi.fn();
vi.mock("react-router-dom", () => ({
  useNavigate: () => mockedNavigate,
}));

describe("Landing page rendering", () => {
  it("Redirect button", () => {
    render(<HomePage />);
    const button = screen.getByText("Get Started");
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(mockedNavigate).toHaveBeenCalledWith("/report", { state: null });
  });
});
