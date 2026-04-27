import { redirect } from "next/navigation";

export default function ResumesPage() {
  redirect("/dashboard/studio?mode=resume");
}
