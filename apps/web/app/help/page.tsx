import { Card } from "@/components/common/Card";

export default function HelpPage() {
  return (
    <div className="max-w-2xl space-y-4">
      <h1 className="text-2xl font-semibold">Help</h1>
      <Card className="space-y-4 p-6">
        <p className="text-muted">AutoEdit AI is a batch editor, not a timeline. The workflow is:</p>
        <ol className="list-decimal space-y-2 pl-5 text-sm">
          <li>Record talking-head clips — in Google Drive, or on your phone if you're using the Eren app.</li>
          <li>Sign in here with that Google account.</li>
          <li>Tap Create, add your footage, then Let Eren edit.</li>
          <li>You can leave while workers transcribe, plan, overlay B-roll, mix audio, and render.</li>
          <li>Come back to preview and download 1080×1920 MP4s.</li>
        </ol>
        <p className="text-sm text-muted">
          Failed videos can be retried individually. Completed stages (transcript, plan, cached B-roll) are reused when possible.
        </p>
      </Card>
    </div>
  );
}

