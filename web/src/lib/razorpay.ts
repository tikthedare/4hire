export function loadRazorpay(): Promise<void> {
  if (window.Razorpay) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(
      'script[src="https://checkout.razorpay.com/v1/checkout.js"]',
    );
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error("Could not load Razorpay Checkout.")));
      return;
    }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Could not load Razorpay Checkout."));
    document.body.appendChild(script);
  });
}

export type CheckoutResult = {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
};

export function openRazorpayCheckout(options: {
  keyId: string;
  amountPaise: number;
  orderId: string;
  description: string;
}): Promise<CheckoutResult> {
  const Razorpay = window.Razorpay;
  if (!Razorpay) return Promise.reject(new Error("Razorpay Checkout is unavailable."));
  return new Promise((resolve, reject) => {
    const checkout = new Razorpay({
      key: options.keyId,
      amount: options.amountPaise,
      currency: "INR",
      order_id: options.orderId,
      name: "ForHire India",
      description: options.description,
      handler: (response) => resolve(response),
      modal: { ondismiss: () => reject(new Error("Checkout closed.")) },
    });
    checkout.open();
  });
}
