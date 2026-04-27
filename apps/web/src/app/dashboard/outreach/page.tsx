import { redirect } from "next/navigation";

export default function OutreachPage() {
  redirect("/dashboard/studio?mode=outreach");
}
