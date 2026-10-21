from cv2.typing import MatLike

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.screen.screen_utils import find_template_coord_in_area
from one_dragon.utils import cv2_utils
from one_dragon.utils.log_utils import log
from zzz_lv.context.zzz_context import ZContext
from zzz_lv.game_data.mini_map_wrapper import MiniMapWrapper


class MiniMapService:

    # 小地图相对于"地图"按钮的偏移量（通过开发工具测量得出）
    # 小地图坐标 = "地图"坐标 - DELTA
    MINI_MAP_DELTA = (169, 151)

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx

        # 小地图动态裁剪区域缓存；按大世界类型复用。
        self._mini_map_rect: Rect | None = None
        self._mini_map_screen_name: str | None = None

    def cut_mini_map(self, screen: MatLike) -> MiniMapWrapper:
        return self.cut_mini_map_with_dynamic_rect(screen)[0]

    def cut_mini_map_with_dynamic_rect(self, screen: MatLike) -> tuple[MiniMapWrapper, Rect | None]:
        """
        截取小地图

        优先复用当前大世界类型对应的动态裁剪区域缓存；没有缓存时通过"地图"按钮模板匹配计算裁剪区域；
        匹配失败时使用`大世界/小地图`静态框兜底。
        注意: 2.8版本更新后, 勘域小地图相对于普通的要更往下17px, 静态框来源于勘域小地图

        Args:
            screen: 游戏画面

        Returns:
            MiniMapWrapper: 小地图图片
            Rect | None: 动态裁剪区域；静态兜底时返回 None
        """
        current_screen_name = self.ctx.screen_loader.current_screen_name
        mini_map_screen_name = current_screen_name if current_screen_name in ['大世界-普通', '大世界-勘域'] else None
        if mini_map_screen_name is not None and self._mini_map_rect is not None and self._mini_map_screen_name == mini_map_screen_name:
            rgb = cv2_utils.crop_image_only(screen, self._mini_map_rect)
            return MiniMapWrapper(rgb), self._mini_map_rect

        # 获取小地图静态配置，用于动态框尺寸和兜底裁剪。
        default_area = self.ctx.screen_loader.get_area('大世界', '小地图')
        mini_map_width = default_area.rect.width
        mini_map_height = default_area.rect.height

        # 使用模板匹配定位"地图"；模板区域统一复用"大世界/地图"
        map_result = find_template_coord_in_area(self.ctx, screen, '大世界', '地图')

        if map_result is not None:
            # 通过匹配坐标 - delta 值计算小地图区域（注意是减法！）
            mini_map_x = map_result.x - self.MINI_MAP_DELTA[0]
            mini_map_y = map_result.y - self.MINI_MAP_DELTA[1]

            # 生成裁剪区域
            mini_map_rect = Rect(
                mini_map_x,
                mini_map_y,
                mini_map_x + mini_map_width,
                mini_map_y + mini_map_height
            )

            # 使用计算出的区域裁剪，确认确实是小地图后才缓存；静态兜底不缓存
            rgb = cv2_utils.crop_image_only(screen, mini_map_rect)
            mini_map = MiniMapWrapper(rgb)
            if mini_map.play_mask_found and mini_map_screen_name is not None:
                self._mini_map_rect = mini_map_rect
                self._mini_map_screen_name = mini_map_screen_name
            log.info(f'[小地图] 动态匹配小地图坐标: ({mini_map_rect.x1}, {mini_map_rect.y1}) - ({mini_map_rect.x2}, {mini_map_rect.y2})')

            return mini_map, mini_map_rect
        else:
            # 模板匹配失败，降级使用固定区域（不缓存）
            rgb = cv2_utils.crop_image_only(screen, default_area.rect)
            return MiniMapWrapper(rgb), None
