import { useState } from "react";
import { useForm, type UseFormRegisterReturn } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Eye, EyeOff, ArrowRight, FlaskConical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ErrorNotice } from "@/components/shared";
import { characters } from "@/lib/characters";
import { getApi, isMock } from "@/services/api";
export const authSchema = z.object({
  email: z.email("auth.emailInvalid"),
  password: z.string().min(8, "auth.passwordMin"),
  confirmPassword: z.string(),
  ageConfirmed: z.boolean(),
  termsAccepted: z.boolean(),
});
export const registrationSchema = authSchema.superRefine((v, ctx) => {
  if (v.password !== v.confirmPassword)
    ctx.addIssue({ code: "custom", path: ["confirmPassword"], message: "auth.mismatch" });
  if (!v.ageConfirmed)
    ctx.addIssue({ code: "custom", path: ["ageConfirmed"], message: "auth.consent" });
  if (!v.termsAccepted)
    ctx.addIssue({ code: "custom", path: ["termsAccepted"], message: "auth.consent" });
});
type Values = z.infer<typeof authSchema>;
function PasswordInput({
  field,
  label,
  error,
}: {
  field: UseFormRegisterReturn;
  label: string;
  error: string | undefined;
}) {
  const [visible, setVisible] = useState(false);
  const { t } = useTranslation();
  return (
    <div>
      <label htmlFor={field.name}>{label}</label>
      <div className="password-field">
        <input
          id={field.name}
          autoComplete={field.name === "confirmPassword" ? "new-password" : "current-password"}
          type={visible ? "text" : "password"}
          {...field}
        />
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label={t(visible ? "auth.hide" : "auth.show")}
          onClick={() => setVisible(!visible)}
        >
          {visible ? <EyeOff /> : <Eye />}
        </Button>
      </div>
      {error && <p className="form-error">{t(error)}</p>}
    </div>
  );
}
export function AuthPage({ registration = false }: { registration?: boolean }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [error, setError] = useState<unknown>(null);
  const [demoBusy, setDemoBusy] = useState(false);
  const form = useForm<Values>({
    resolver: zodResolver(registration ? registrationSchema : authSchema),
    defaultValues: {
      email: "",
      password: "",
      confirmPassword: "",
      ageConfirmed: false,
      termsAccepted: false,
    },
  });
  const submit = async (v: Values) => {
    setError(null);
    try {
      const user = registration
        ? await getApi().register(v.email, v.password, v.ageConfirmed, v.termsAccepted)
        : await getApi().login(v.email, v.password);
      qc.clear();
      qc.setQueryData(["session"], user);
      await navigate({ to: user.admin ? "/admin" : "/wallet" });
    } catch (e) {
      setError(e);
    }
  };
  const demo = async (admin: boolean) => {
    setDemoBusy(true);
    await submit({
      email: admin ? "admin@nexusai.app" : "demo@nexusai.app",
      password: "demo1234",
      confirmPassword: "",
      ageConfirmed: true,
      termsAccepted: true,
    });
    setDemoBusy(false);
  };
  const errors = form.formState.errors;
  return (
    <main className="form-page">
      <div className="auth-art">
        <img src={characters[1]?.image} alt="Luna — personnage IA NexusAI" />
        <div className="auth-art-caption">
          <span className="eyebrow">NEXUSAI</span>
          <h2>{t("landing.subtitle")}</h2>
          <p className="text-muted-foreground text-xs">
            {t("landing.noCard")} · {t("landing.welcome")}
          </p>
        </div>
      </div>
      <div>
        <span className="eyebrow">NEXUSAI WORKSPACE</span>
        <h1 className="page-title mt-4">
          {t(registration ? "auth.titleRegister" : "auth.titleLogin")}
        </h1>
        <p className="page-subtitle">
          {t(registration ? "auth.subtitleRegister" : "auth.subtitleLogin")}
        </p>
        {error ? (
          <div className="mb-5">
            <ErrorNotice error={error} />
          </div>
        ) : null}
        <form className="form-stack" onSubmit={form.handleSubmit(submit)} noValidate>
          <div>
            <label htmlFor="email">{t("auth.email")}</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="vous@exemple.com"
              {...form.register("email")}
            />
            {errors.email?.message && <p className="form-error">{t(errors.email.message)}</p>}
          </div>
          <PasswordInput
            field={form.register("password")}
            label={t("auth.password")}
            error={errors.password?.message}
          />
          {registration && (
            <>
              <PasswordInput
                field={form.register("confirmPassword")}
                label={t("auth.confirmPassword")}
                error={errors.confirmPassword?.message}
              />
              <div>
                <label className="check-label">
                  <input type="checkbox" {...form.register("ageConfirmed")} />
                  <span>{t("auth.age")}</span>
                </label>
                {errors.ageConfirmed?.message && (
                  <p className="form-error">{t(errors.ageConfirmed.message)}</p>
                )}
                <p className="text-muted-foreground text-[10px] ml-7">{t("auth.ageNote")}</p>
              </div>
              <div>
                <label className="check-label">
                  <input type="checkbox" {...form.register("termsAccepted")} />
                  <span>{t("auth.terms")}</span>
                </label>
                {errors.termsAccepted?.message && (
                  <p className="form-error">{t(errors.termsAccepted.message)}</p>
                )}
              </div>
            </>
          )}
          <Button size="lg" type="submit" disabled={form.formState.isSubmitting || demoBusy}>
            {t(registration ? "auth.register" : "auth.login")}
            <ArrowRight />
          </Button>
        </form>
        {!registration && (
          <details className="text-xs text-muted-foreground mt-5">
            <summary className="cursor-pointer">{t("auth.forgot")}</summary>
            <p className="mt-3 leading-7">{t("auth.forgotNote")}</p>
          </details>
        )}
        <p className="text-xs text-muted-foreground mt-6">
          {t(registration ? "auth.hasAccount" : "auth.noAccount")}{" "}
          <Link className="text-violet" to={registration ? "/login" : "/register"}>
            {t(registration ? "auth.login" : "auth.register")}
          </Link>
        </p>
        {isMock && (
          <>
            <div className="border-t border-border pt-5 mt-6 flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={demoBusy || form.formState.isSubmitting}
                onClick={() => void demo(false)}
              >
                <FlaskConical />
                {t("demo.account")}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                disabled={demoBusy || form.formState.isSubmitting}
                onClick={() => void demo(true)}
              >
                {t("demo.admin")}
              </Button>
            </div>
            <p className="text-[10px] text-muted-foreground leading-6 mt-4">{t("demo.notice")}</p>
          </>
        )}
      </div>
    </main>
  );
}
