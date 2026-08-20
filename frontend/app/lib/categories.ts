export interface Category {
  name: string;
  seriesIds: string[];
}

export const CATEGORIES: Category[] = [
  {
    name: "增长类指标",
    seriesIds: ["GDPC1", "GDPNOW", "MANEMP", "NAPMNOI", "NAPMII", "INDPRO", "TCU", "RSAFS", "DGORDER"],
  },
  {
    name: "通胀类指标",
    seriesIds: ["CPIAUCSL", "CPILFESL", "PCEPILFE", "T5YIE", "PPIACO", "CES0500000003"],
  },
  {
    name: "就业类指标",
    seriesIds: ["PAYEMS", "UNRATE", "SAHMREALTIME", "ICSA", "CCSA", "JTSJOL", "JTSQUR", "CIVPART"],
  },
  {
    name: "货币政策与利率",
    seriesIds: ["FEDFUNDS", "DGS10", "T10Y2Y", "DFII10", "M2SL", "WALCL"],
  },
  {
    name: "信用与金融压力",
    seriesIds: ["BAMLC0A0CM", "BAMLH0A0HYM2", "DCPF3M", "STLFSI4"],
  },
  {
    name: "市场信号与情绪",
    seriesIds: ["VIXCLS"],
  },
  {
    name: "库存与投资周期",
    seriesIds: ["ISRATIO", "HOUST", "PERMIT", "NEWORDER"],
  },
  {
    name: "全球与外部冲击",
    seriesIds: ["DTWEXBGS"],
  },
];
