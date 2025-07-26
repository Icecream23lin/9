import CustomAlert from "./CustomAlert";
function UploadAlerts({ successfulUpdate, errorflag, onClose, errorMessage }) {
  return (
    <>
      <CustomAlert
        severity="success"
        flag={successfulUpdate && !errorflag}
        number={1}
        onClose={onClose}
      >
        Data Validation success
      </CustomAlert>
      <CustomAlert
        severity="success"
        flag={successfulUpdate && !errorflag}
        number={2}
        onClose={onClose}
      >
        Data upload success.
      </CustomAlert>
      <CustomAlert
        severity="warning"
        flag={errorflag}
        number={1}
        onClose={onClose}
      >
        {errorMessage}
      </CustomAlert>
      <CustomAlert
        severity="error"
        flag={errorflag}
        number={2}
        onClose={onClose}
      >
        Data upload failed.
      </CustomAlert>
    </>
  );
}
export default UploadAlerts;
