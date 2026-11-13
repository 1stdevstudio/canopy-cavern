import gzip,struct,math,json,zipfile,collections,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]/'src/main/resources/data'
class Reader:
 def __init__(self,b): self.b=b; self.i=0
 def read(self,n): out=self.b[self.i:self.i+n]; self.i+=n; return out
 def num(self,fmt): return struct.unpack('>'+fmt,self.read(struct.calcsize(fmt)))[0]
 def string(self): return self.read(self.num('H')).decode('utf-8')
 def payload(self,t):
  if 1<=t<=6:return self.num({1:'b',2:'h',3:'i',4:'q',5:'f',6:'d'}[t])
  if t==7:return self.read(self.num('i'))
  if t==8:return self.string()
  if t==9:
   subtype=self.num('B'); return [self.payload(subtype) for _ in range(self.num('i'))]
  if t==10:
   out={}
   while True:
    subtype=self.num('B')
    if not subtype:return out
    name=self.string();out[name]=self.payload(subtype)
  if t in (11,12):return [self.num('i' if t==11 else 'q') for _ in range(self.num('i'))]
  raise ValueError(t)
def parse(path):
 r=Reader(gzip.decompress(path.read_bytes()));t=r.num('B');r.string();return r.payload(t)
def full_cube(s):
 return s in {'minecraft:stone','minecraft:cobblestone','minecraft:mossy_cobblestone','minecraft:stone_bricks','minecraft:mossy_stone_bricks','minecraft:deepslate_bricks','minecraft:polished_deepslate','minecraft:cobbled_deepslate','minecraft:chiseled_deepslate','minecraft:deepslate_tiles','minecraft:basalt','minecraft:polished_basalt','minecraft:glass','minecraft:tinted_glass','minecraft:cut_copper','minecraft:copper_block','minecraft:sandstone','minecraft:smooth_sandstone','minecraft:red_sandstone','minecraft:smooth_red_sandstone','minecraft:dirt','minecraft:grass_block','minecraft:gravel','minecraft:clay','minecraft:obsidian','minecraft:iron_block','minecraft:gold_block','minecraft:bricks','minecraft:packed_ice','minecraft:blue_ice','minecraft:cut_sandstone','minecraft:terracotta','minecraft:moss_block','minecraft:shroomlight','minecraft:mud_bricks'} or s.endswith(('_planks','_log','_wood','_terracotta','_stained_glass','_concrete','_wool'))
DIMS={'minecraft:iron_golem':(1.4,2.7),'minecraft:pillager':(.6,1.95),'minecraft:villager':(.6,1.95),'minecraft:zombie_villager':(.6,1.95),'canopycavern:village_sentinel':(.6,1.95)}
errors=[]; collisions=[];hazards=[];jigsaw_errors=[];loot_missing=[];tot=collections.Counter(); docs={};nbts=list(ROOT.glob('*/structure/**/*.nbt'))
with zipfile.ZipFile(os.environ.get('MINECRAFT_JAR', str(Path.home()/'.gradle/caches/fabric-loom/26.3/minecraft-common.jar'))) as z: vanilla=set(z.namelist())
def exists(rid,kind,suffix):
 ns,key=rid.split(':',1) if ':' in rid else ('minecraft',rid)
 return (ROOT/ns/kind/(key+suffix)).exists() or (ns=='minecraft' and f'data/minecraft/{kind}/{key}{suffix}' in vanilla)
for p in nbts:
 rel=str(p.relative_to(ROOT));d=parse(p);docs[rel]=d;size=d['size']
 palettes=d['palettes'] if 'palettes' in d else [d['palette']]
 if not palettes or not palettes[0] or any(len(variant)!=len(palettes[0]) for variant in palettes):
  errors.append((rel,'invalid palette variants'));continue
 pal=palettes[0]
 if any(not 0<=b['state']<len(pal) for b in d['blocks']):
  errors.append((rel,'out of bounds palette index'));continue
 blocks={tuple(b['pos']):pal[b['state']] for b in d['blocks']}
 tot['blocks']+=len(d['blocks']);tot['entities']+=len(d.get('entities',[]));tot['golems']+=sum(e['nbt']['id']=='minecraft:iron_golem' for e in d.get('entities',[]))
 if len(blocks)!=len(d['blocks']):errors.append((rel,'duplicate coordinates'))
 for b in d['blocks']:
  if not all(0<=v<size[i] for i,v in enumerate(b['pos'])):errors.append((rel,'out of bounds',b['pos']))
  state=pal[b['state']]; bid=state.get('id',state.get('Name')); n=b.get('nbt',{})
  if bid=='minecraft:structure_void':errors.append((rel,'structure_void stored',b['pos']))
  if bid=='minecraft:jigsaw':
   tot['jigsaws']+=1
   missing=set(['pool','name','target','final_state'])-n.keys()
   if missing:jigsaw_errors.append((rel,b['pos'],sorted(missing)))
   if n.get('pool') not in (None,'minecraft:empty') and not exists(n['pool'],'worldgen/template_pool','.json'):jigsaw_errors.append((rel,b['pos'],'missing pool',n['pool']))
  if 'LootTable' in n:
   tot['loot_chests']+=1
   if not exists(n['LootTable'],'loot_table','.json'):loot_missing.append((rel,b['pos'],n['LootTable']))
 for e in d.get('entities',[]):
  eid=e['nbt']['id'];pos=e['pos'];bp=e['blockPos']
  if eid in DIMS:
   w,h=DIMS[eid];minp=[pos[0]-w/2,pos[1],pos[2]-w/2];maxp=[pos[0]+w/2,pos[1]+h,pos[2]+w/2]
   hits=[]
   for x in range(math.floor(minp[0]),math.ceil(maxp[0])):
    for y in range(math.floor(minp[1]),math.ceil(maxp[1])):
     for z in range(math.floor(minp[2]),math.ceil(maxp[2])):
      b=blocks.get((x,y,z),{});bid=b.get('id',b.get('Name','<absent>'))
      if full_cube(bid):hits.append(((x,y,z),bid))
   if hits:collisions.append((rel,eid,pos,hits))
   for dy in (0,-1):
    xyz=(math.floor(pos[0]),math.floor(pos[1])+dy,math.floor(pos[2]));b=blocks.get(xyz,{});bid=b.get('id',b.get('Name','<absent>'))
    props=b.get('properties',b.get('Properties',{}))
    if bid in ('minecraft:fire','minecraft:soul_fire','minecraft:lava','minecraft:magma_block','minecraft:cactus') or (bid in ('minecraft:campfire','minecraft:soul_campfire') and props.get('lit','true')=='true'):hazards.append((rel,eid,pos,xyz,bid))
# recursively resolve all custom template-pool references
pool_errors=[];pool_count=0
for p in ROOT.glob('*/worldgen/template_pool/**/*.json'):
 pool_count+=1;d=json.loads(p.read_text())
 def check(e):
  kind=e.get('element_type','')
  if kind.endswith('list_pool_element'):
   for child in e.get('elements',[]):check(child)
  elif kind.endswith(('single_pool_element','legacy_single_pool_element')):
   loc=e.get('location')
   if loc and not exists(loc,'structure','.nbt'):pool_errors.append((str(p.relative_to(ROOT)),'missing template',loc))
  pro=e.get('processors')
  if isinstance(pro,str) and not exists(pro,'worldgen/processor_list','.json'):pool_errors.append((str(p.relative_to(ROOT)),'missing processor',pro))
 for elem in d.get('elements',[]):check(elem['element'])
 fall=d.get('fallback')
 if fall and fall!='minecraft:empty' and not exists(fall,'worldgen/template_pool','.json'):pool_errors.append((str(p.relative_to(ROOT)),'missing fallback',fall))
print('TOTAL',len(nbts),'templates',dict(tot),'pools',pool_count)
print('geometry_errors',errors[:10],'count',len(errors))
print('full_cube_collisions_count',len(collisions),'by_entity',dict(collections.Counter(c[1] for c in collisions)))
for c in collisions: print('COLLISION',c)
print('HAZARDS',hazards)
print('JIGSAW_ERRORS',jigsaw_errors)
print('MISSING_LOOT',loot_missing)
print('POOL_ERRORS',pool_errors)
raise SystemExit(1 if errors or collisions or hazards or jigsaw_errors or loot_missing or pool_errors else 0)
