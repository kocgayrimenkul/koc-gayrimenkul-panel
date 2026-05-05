# -*- coding: utf-8 -*-
import os
import sys

path = r"apps\templates\portfolio\property_list.html"

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# ============ 1) SEKMELER ============
old_tabs = '''            <button type="button" class="px-3 py-1.5 text-xs font-semibold flex items-center rounded-lg bg-blue-600 text-white shadow-sm">
                <i class="fas fa-home mr-1.5 text-[11px]"></i> Kendi Portföylerim
                <span class="ml-2 bg-white/20 text-white px-1.5 py-0.5 rounded text-[10px] font-bold">{{ properties|length }}</span>
            </button>
            <button type="button" class="px-3 py-1.5 text-xs font-medium flex items-center rounded-lg text-slate-500 bg-white border border-slate-200 hover:bg-slate-100 transition">
                <i class="fas fa-building mr-1.5 text-[11px]"></i> Ofis Portföyleri
                <span class="ml-2 bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded text-[10px] font-bold">0</span>
            </button>'''

new_tabs = '''            {% if is_consultant %}
            <a href="?tab=own" class="px-3 py-1.5 text-xs font-semibold flex items-center rounded-lg {% if active_tab == 'own' %}bg-blue-600 text-white shadow-sm{% else %}text-slate-500 bg-white border border-slate-200 hover:bg-slate-100{% endif %} transition no-underline">
                <i class="fas fa-home mr-1.5 text-[11px]"></i> Kendi Portföylerim
                <span class="ml-2 {% if active_tab == 'own' %}bg-white/20 text-white{% else %}bg-blue-50 text-blue-600{% endif %} px-1.5 py-0.5 rounded text-[10px] font-bold">{{ own_count }}</span>
            </a>
            <a href="?tab=office" class="px-3 py-1.5 text-xs font-semibold flex items-center rounded-lg {% if active_tab == 'office' %}bg-blue-600 text-white shadow-sm{% else %}text-slate-500 bg-white border border-slate-200 hover:bg-slate-100{% endif %} transition no-underline">
                <i class="fas fa-building mr-1.5 text-[11px]"></i> Ofis Portföyleri
                <span class="ml-2 {% if active_tab == 'office' %}bg-white/20 text-white{% else %}bg-slate-100 text-slate-500{% endif %} px-1.5 py-0.5 rounded text-[10px] font-bold">{{ office_count }}</span>
            </a>
            {% else %}
            <span class="px-3 py-1.5 text-xs font-semibold flex items-center rounded-lg bg-blue-600 text-white shadow-sm">
                <i class="fas fa-home mr-1.5 text-[11px]"></i> Tüm Portföyler
                <span class="ml-2 bg-white/20 text-white px-1.5 py-0.5 rounded text-[10px] font-bold">{{ properties|length }}</span>
            </span>
            {% endif %}'''

if old_tabs in c:
    c = c.replace(old_tabs, new_tabs)
    print("OK: Sekmeler degistirildi")
else:
    print("HATA: Sekme blogu bulunamadi!")
    sys.exit(1)

# ============ 2) MULK SAHIBI ============
old_owner = '''<div class="text-[10px] text-slate-400 uppercase font-bold leading-none mb-0.5">MÜLK SAHİBİ</div>
                                <div class="text-[13px] font-bold">{{ property.owner_name|default:"Atanmamış" }}</div>'''

new_owner = '''<div class="text-[10px] text-slate-400 uppercase font-bold leading-none mb-0.5">MÜLK SAHİBİ</div>
                                {% if is_office_view %}
                                    <div class="text-[13px] font-bold text-slate-300 italic flex items-center gap-1" title="Bu portföy sizin mahallenize ait değil">
                                        <i class="fas fa-lock text-[10px]"></i> Gizli
                                    </div>
                                {% else %}