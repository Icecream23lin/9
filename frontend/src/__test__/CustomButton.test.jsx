import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import CustomButton from "../Components/CustomButton";

const mockedNavigate = vi.fn();
vi.mock("react-router-dom", () => ({
  useNavigate: () => mockedNavigate,
}));

describe("CustomButton rendering test", () => {
  it("Custom button is rendered with appropriate title", () => {
    render(<CustomButton title="Button value" navigateTo="" />);
    expect(screen.getByText("Button value")).toBeInTheDocument();
  });
});

describe("Navigate works", () => {
  it("Clicking on button navigates to appropriate link", () => {
    render(<CustomButton title="Generate report" navigateTo="/report" />);
    fireEvent.click(screen.getByText("Generate report"));
    expect(mockedNavigate).toHaveBeenCalledWith("/report", { state: null });
  });
});

describe("Button disable works", () => {
  it("Button should be disabled when disabled attribute is passed", () => {
    render(
      <CustomButton
        title="Generate report"
        navigateTo="/report"
        disabled={true}
      />
    );
    const button = screen.getByText("Generate report");
    expect(button).toBeDisabled();
  });
});
