import { act, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import CustomAlert from "../Components/CustomAlert";

describe("CustomAlert rendering test", () => {
  it("Custom alert is rendered when flag turns true", () => {
    let flag = true;
    render(
      <CustomAlert
        flag={flag}
        number={1}
        severity="warning"
        onClose={() => {
          flag = false;
        }}
      >
        Test alert message
      </CustomAlert>
    );
    const alertmessage = screen.getByText("Test alert message");
    expect(alertmessage).toBeInTheDocument();
  });
});

describe("Autohide alert message", () => {
  it("Alert is hidden after 2 seconds", async () => {
    vi.useFakeTimers();
    let flag = true;
    act(() => {
      render(
        <CustomAlert
          flag={flag}
          number={1}
          onClose={() => {
            flag = false;
          }}
        >
          Test alert message
        </CustomAlert>
      );
    });

    const alertmessage = screen.getByText("Test alert message");
    expect(alertmessage).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(2600);
    });

    expect(flag == false);

    vi.useRealTimers();
  });
});
