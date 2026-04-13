import Script from "next/script";

/**
 * Speculation Rules API — prefetch/prerender các route phổ biến để navigation
 * hầu như instant. Chrome/Edge hỗ trợ; Firefox/Safari ignore nhưng không lỗi.
 *
 * Docs: https://developer.mozilla.org/en-US/docs/Web/API/Speculation_Rules_API
 *
 * Chiến lược:
 * - prerender (moderate): các route được hover — Chrome tự động kích hoạt khi
 *   link được hover ~200ms. Loại trừ /logout và các route mutation.
 * - prefetch (moderate): các route landing chính — tải HTML sẵn nhưng chưa
 *   render, tiết kiệm bandwidth so với prerender.
 */
const RULES = {
  prerender: [
    {
      where: {
        and: [
          { href_matches: "/*" },
          { not: { href_matches: "/logout" } },
          { not: { href_matches: "/api/*" } },
        ],
      },
      eagerness: "moderate",
    },
  ],
  prefetch: [
    {
      urls: ["/login", "/register", "/member", "/merchant", "/admin"],
      eagerness: "moderate",
    },
  ],
};

export function SpeculationRules() {
  return (
    <Script
      id="speculation-rules"
      type="speculationrules"
      strategy="afterInteractive"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(RULES) }}
    />
  );
}
