<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.10.2" name="test_tileset" tilewidth="16" tileheight="16" tilecount="16" columns="4">
 <image source="test_tileset.png" width="64" height="64"/>
 <properties>
  <property name="author" value="test"/>
  <property name="version" type="int" value="1"/>
 </properties>
 <tile id="0">
  <properties>
   <property name="terrain" value="grass"/>
   <property name="walkable" type="bool" value="true"/>
  </properties>
  <animation>
   <frame tileid="0" duration="500"/>
   <frame tileid="4" duration="500"/>
  </animation>
 </tile>
 <tile id="1">
  <properties>
   <property name="terrain" value="dirt"/>
  </properties>
 </tile>
 <wangsets>
  <wangset name="terrain" type="corner" tile="-1">
   <wangcolor name="Grass" color="#00ff00" tile="0" probability="1"/>
   <wangcolor name="Dirt" color="#8b4513" tile="1" probability="1"/>
   <wangtile tileid="0" wangid="0,1,0,1,0,1,0,1"/>
   <wangtile tileid="1" wangid="0,2,0,2,0,2,0,2"/>
   <wangtile tileid="8" wangid="0,2,0,1,0,1,0,1"/>
   <wangtile tileid="9" wangid="0,1,0,1,0,1,0,2"/>
   <wangtile tileid="10" wangid="0,1,0,1,0,2,0,1"/>
   <wangtile tileid="11" wangid="0,1,0,2,0,1,0,1"/>
  </wangset>
 </wangsets>
</tileset>
