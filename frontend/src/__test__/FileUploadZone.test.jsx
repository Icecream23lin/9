import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";
import FileUploadZone from "../Components/FileUploadZone";

describe("FileUploadZone renders properly", () => {
  test("accepts files via input change", async () => {
    const onFilesAccepted = vi.fn();
    render(<FileUploadZone onFilesAccepted={onFilesAccepted} maxFiles={1} />);

    expect(screen.getByText("Upload files")).toBeInTheDocument();

    const input = screen
      .getByTestId("dropzone")
      .querySelector('input[type="file"]');

    const file = new File(["xyz"], "test.csv", { type: "text/csv" });

    await waitFor(() =>
      fireEvent.change(input, {
        target: { files: [file] },
      })
    );

    expect(onFilesAccepted).toHaveBeenCalledTimes(1);
    expect(onFilesAccepted).toHaveBeenCalledWith(
      expect.arrayContaining([file])
    );
  });
});

describe("FileUploadZone should restrict number of files", () => {
  test("accepts only max number of files", async () => {
    const onFilesAccepted = vi.fn();
    render(<FileUploadZone onFilesAccepted={onFilesAccepted} maxFiles={1} />);

    const input = screen
      .getByTestId("dropzone")
      .querySelector('input[type="file"]');

    const file = new File(["xyz"], "test.csv", { type: "text/csv" });

    await waitFor(() =>
      fireEvent.change(input, {
        target: { files: [file] },
      })
    );
    expect(onFilesAccepted).toHaveBeenCalledWith(
      expect.arrayContaining([file])
    );
    await waitFor(() =>
      fireEvent.change(input, {
        target: { files: [file] },
      })
    );

    expect(onFilesAccepted).toHaveBeenCalledTimes(2);
    expect(onFilesAccepted).toHaveBeenCalledWith(expect.arrayContaining([]));
  });
});
