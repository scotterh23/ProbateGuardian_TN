const ITEMS: { term: string; body: string }[] = [
  {
    term: "Letters Testamentary / Letters of Administration",
    body: "Court papers that name who may act for the estate. “Testamentary” is used when there is a will; “Administration” when there is not. Until Letters are issued, no one usually has authority to list or sell the house. This is information, not legal advice — your probate attorney confirms what your court requires.",
  },
  {
    term: "Inventory",
    body: "A snapshot of what the estate owns: the house, bank accounts, vehicles, and other assets. It helps the court, the executor, and the family see the same picture.",
  },
  {
    term: "Creditor Period",
    body: "In Tennessee, notice to creditors is generally published once a week for two consecutive weeks. Creditors then generally have four months from the first publication to make claims. A house can still sell before that window ends, but it is often riskier. The safer window to close is after the four months, always subject to court approval. This is not legal advice — your attorney confirms the dates for this estate.",
  },
  {
    term: "Final Accounting",
    body: "A report of money in, bills paid, and what is left. The court reviews it before the estate can be closed and remaining assets distributed.",
  },
  {
    term: "Testate vs Intestate",
    body: "Testate means there is a valid will. Intestate means there is not, so Tennessee’s default inheritance rules generally decide who receives what. Either path still goes through probate when real estate is involved.",
  },
  {
    term: "Why the house can close before the entire estate is closed",
    body: "Selling the house and finishing probate are related but not the same timeline. Once someone has Letters, the property can often be listed and, with court awareness, sold. The estate itself stays open until inventory, creditors, taxes, and a final accounting are handled. A house closing does not automatically close the probate case.",
  },
];

export function EstateGlossary() {
  return (
    <section className="card p-5">
      <h2 className="font-serif text-xl">FAQ & glossary</h2>
      <p className="mt-1 text-sm text-muted">
        Plain-language notes for families. This is not legal advice. Your probate attorney and the
        court have the final word.
      </p>
      <div className="mt-4 divide-y divide-line">
        {ITEMS.map((item) => (
          <details key={item.term} className="group py-3">
            <summary className="cursor-pointer list-none font-semibold text-forest marker:content-none">
              <span className="mr-2 text-accent group-open:hidden">+</span>
              <span className="mr-2 hidden text-accent group-open:inline">−</span>
              {item.term}
            </summary>
            <p className="mt-2 text-sm text-muted">{item.body}</p>
          </details>
        ))}
      </div>
    </section>
  );
}
