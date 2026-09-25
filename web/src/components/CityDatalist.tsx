import { INDIAN_CITIES, INDIAN_CITIES_DATALIST_ID } from "../lib/indian-cities";

type Props = {
  id?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  className?: string;
};

export function CityDatalist({
  id = "city-input",
  value,
  onChange,
  placeholder = "City",
  className = "",
}: Props) {
  return (
    <>
      <input
        id={id}
        list={INDIAN_CITIES_DATALIST_ID}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={className}
      />
      <datalist id={INDIAN_CITIES_DATALIST_ID}>
        {INDIAN_CITIES.map((c) => (
          <option key={c} value={c} />
        ))}
      </datalist>
    </>
  );
}
