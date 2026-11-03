import * as React from "react";

// Card
/**
 * Story / resource card: optional image, eyebrow, condensed headline, body.
 * @startingPoint section="Content" subtitle="Story cards for news, bright spots and resources" viewport="700x420"
 */
export interface CardProps {
  image?: string;
  imageAlt?: string;
  eyebrow?: string;
  title?: React.ReactNode;
  body?: React.ReactNode;
  footer?: React.ReactNode;
  /** Ground color */
  tone?: "white" | "sand" | "navy" | "sky";
  /** Adds paper shadow + masking-tape strip (Human Touch collage feel) */
  taped?: boolean;
  href?: string;
  style?: React.CSSProperties;
}
export declare function Card(props: CardProps): JSX.Element;

// PullQuote
export interface PullQuoteProps {
  quote: React.ReactNode;
  name?: string;
  role?: string;
  tone?: "navy" | "sky" | "sand" | "white";
  style?: React.CSSProperties;
}
export declare function PullQuote(props: PullQuoteProps): JSX.Element;

// StatCallout
/**
 * Big-number data callout (Bright Data pillar).
 * @startingPoint section="Content" subtitle="Big-number stat blocks" viewport="700x220"
 */
export interface StatCalloutProps {
  value: React.ReactNode;
  label: React.ReactNode;
  source?: React.ReactNode;
  tone?: "sky" | "navy" | "sand" | "white" | "lime";
  align?: "left" | "center";
  style?: React.CSSProperties;
}
export declare function StatCallout(props: StatCalloutProps): JSX.Element;

// Button
/**
 * Pill-shaped action button. Asap Condensed Bold, uppercase.
 * @startingPoint section="Core" subtitle="Pill buttons in brand variants" viewport="700x260"
 */
export interface ButtonProps {
  /** primary = navy; brand = sky; highlight = sunshine; outline; inverse (on dark); ghost */
  variant?: "primary" | "brand" | "highlight" | "outline" | "inverse" | "ghost";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
  fullWidth?: boolean;
  /** Renders as <a> when set */
  href?: string;
  onClick?: (e: React.MouseEvent) => void;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}
export declare function Button(props: ButtonProps): JSX.Element;

// IconButton
export interface IconButtonProps {
  icon: React.ReactNode;
  /** Accessible label (also tooltip title) */
  label: string;
  variant?: "primary" | "brand" | "outline" | "ghost" | "inverse";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  onClick?: (e: React.MouseEvent) => void;
  style?: React.CSSProperties;
}
export declare function IconButton(props: IconButtonProps): JSX.Element;

// Tag
export interface TagProps {
  tone?: "sky" | "navy" | "sunshine" | "coral" | "lime" | "sand" | "outline";
  size?: "sm" | "md";
  children?: React.ReactNode;
  style?: React.CSSProperties;
}
export declare function Tag(props: TagProps): JSX.Element;

// Dialog
export interface DialogProps {
  open?: boolean;
  title?: React.ReactNode;
  children?: React.ReactNode;
  actions?: React.ReactNode;
  onClose?: () => void;
  width?: number;
  /** Render without fixed scrim (for docs/previews) */
  inline?: boolean;
}
export declare function Dialog(props: DialogProps): JSX.Element | null;

// Toast
export interface ToastProps {
  tone?: "info" | "success" | "warning" | "danger";
  title?: React.ReactNode;
  children?: React.ReactNode;
  onClose?: () => void;
  style?: React.CSSProperties;
}
export declare function Toast(props: ToastProps): JSX.Element;

// Tooltip
export interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  placement?: "top" | "bottom";
  /** Force open (docs) */
  open?: boolean;
}
export declare function Tooltip(props: TooltipProps): JSX.Element;

// Checkbox
export interface CheckboxProps {
  label?: React.ReactNode;
  checked?: boolean;
  defaultChecked?: boolean;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  disabled?: boolean;
  /** Render as radio (prefer the Radio export) */
  radio?: boolean;
  name?: string;
  value?: string;
  style?: React.CSSProperties;
}
export declare function Checkbox(props: CheckboxProps): JSX.Element;
export declare function Radio(props: Omit<CheckboxProps, "radio">): JSX.Element;

// Input
/**
 * Text field with uppercase condensed label.
 * @startingPoint section="Forms" subtitle="Inputs, selects and toggles" viewport="700x380"
 */
export interface InputProps {
  label?: string;
  helper?: string;
  /** Error message; turns the border coral-red */
  error?: string;
  placeholder?: string;
  value?: string;
  defaultValue?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  type?: string;
  disabled?: boolean;
  multiline?: boolean;
  rows?: number;
  id?: string;
  style?: React.CSSProperties;
}
export declare function Input(props: InputProps): JSX.Element;

// Select
export interface SelectOption { value: string; label: string }
export interface SelectProps {
  label?: string;
  options?: (string | SelectOption)[];
  value?: string;
  defaultValue?: string;
  onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  helper?: string;
  placeholder?: string;
  disabled?: boolean;
  style?: React.CSSProperties;
}
export declare function Select(props: SelectProps): JSX.Element;

// Switch
export interface SwitchProps {
  label?: React.ReactNode;
  checked?: boolean;
  defaultChecked?: boolean;
  onChange?: (checked: boolean) => void;
  disabled?: boolean;
  style?: React.CSSProperties;
}
export declare function Switch(props: SwitchProps): JSX.Element;

// Tabs
export interface TabItem { value: string; label: React.ReactNode }
export interface TabsProps {
  tabs: (string | TabItem)[];
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  /** dark = on navy/sky grounds */
  tone?: "light" | "dark";
  style?: React.CSSProperties;
}
export declare function Tabs(props: TabsProps): JSX.Element;

declare global { interface Window { CommunitySolutionsDesignSystem_01cef0: { Card: typeof Card; PullQuote: typeof PullQuote; StatCallout: typeof StatCallout; Button: typeof Button; IconButton: typeof IconButton; Tag: typeof Tag; Dialog: typeof Dialog; Toast: typeof Toast; Tooltip: typeof Tooltip; Checkbox: typeof Checkbox; Radio: typeof Radio; Input: typeof Input; Select: typeof Select; Switch: typeof Switch; Tabs: typeof Tabs } } }
