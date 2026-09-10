import Header from '../components/layout/Header';
import FileUploadPage from '../components/upload/FileUpload';

export default function UploadPage() {
  return (
    <div>
      <Header title="Ingest Data" subtitle="Upload FIRs, call records, and transaction logs for processing" />
      <FileUploadPage />
    </div>
  );
}
