import { redirect } from "next/navigation";

export default function AnswersPage() {
  redirect("/dashboard/studio?mode=answers");
}
