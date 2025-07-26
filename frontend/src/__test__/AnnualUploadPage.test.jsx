import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AnnualUploadPage from "../Pages/AnnualUploadPage";
import { MemoryRouter } from "react-router-dom";
import { upload_file as mockUploadFile } from "../services";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../services", () => ({
  upload_file: vi.fn(),
}));

// mock components
vi.mock("../Components/CustomAlert", () => {
  return {
    default: (props) => (props.flag ? <div>{props.children}</div> : null),
  };
});

vi.mock("../Components/RecentUploads", () => {
  return {
    default: (props) => <div>{props.children}</div>,
  };
});

vi.mock("../Components/CustomButton", () => {
  return {
    default: (props) => (
      <button disabled={props.disabled}>{props.title}</button>
    ),
  };
});

vi.mock("../Components/FileUploadZone", () => {
  return {
    default: (props) => (
      <button
        onClick={() => props.onFilesAccepted([new File(["file"], "test.xlsx")])}
      >
        Upload
      </button>
    ),
  };
});

describe("AnnualUploadPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("Generate button disabled at start", () => {
    render(
      <MemoryRouter>
        <AnnualUploadPage />
      </MemoryRouter>
    );

    expect(screen.getByText("Generate report")).toBeDisabled();
  });

  it("Upon successful upload show successful alerts", async () => {
    mockUploadFile.mockResolvedValueOnce({
      data: { original_filename: "test.xlsx" },
    });

    render(
      <MemoryRouter>
        <AnnualUploadPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText("Upload"));

    await waitFor(() => {
      expect(screen.getByText("Data Validation success")).toBeInTheDocument();
      expect(screen.getByText("Data upload success.")).toBeInTheDocument();
      expect(screen.getByText("test.xlsx")).toBeInTheDocument();
      expect(screen.getByText("Generate report")).not.toBeDisabled();
    });
  });

  it("shows error alerts on upload failure", async () => {
    mockUploadFile.mockRejectedValueOnce({
      response: { data: { error: "Upload failed due to server error" } },
    });

    render(
      <MemoryRouter>
        <AnnualUploadPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText("Upload"));

    await waitFor(() => {
      expect(
        screen.getByText("Upload failed due to server error")
      ).toBeInTheDocument();
      expect(screen.getByText("Data upload failed.")).toBeInTheDocument();
    });
  });
});

describe("AnnualUploadPage Invalid uploads", () => {
  it("handles invalid file type", async () => {
    vi.resetModules();

    vi.doMock("../Components/FileUploadZone", () => ({
      default: (props) => (
        <button onClick={() => props.onFilesAccepted([])}>
          Invalid Upload
        </button>
      ),
    }));

    const AnnualUploadPageInvalid = (await import("../Pages/AnnualUploadPage"))
      .default;

    render(
      <MemoryRouter>
        <AnnualUploadPageInvalid />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText("Invalid Upload"));

    await waitFor(() => {
      expect(
        screen.getByText(/Invalid file type, please upload/)
      ).toBeInTheDocument();
      expect(screen.getByText("Data upload failed.")).toBeInTheDocument();
    });
  });
});
