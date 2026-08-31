require 'json'

module Jekyll
  class OfficePageGenerator < Generator
    safe true
    priority :normal

    def generate(site)
      offices = load_json(site, '_rawdata/offices.json')

      Jekyll.logger.info "OfficeGenerator:", "#{offices.size}개 농기계임대사업소 페이지 생성 중..."
      offices.each do |o|
        next if o['slug'].to_s.strip.empty?
        site.pages << OfficePage.new(site, o)
      end

      Jekyll.logger.info "OfficeGenerator:", "완료 (#{offices.size}개)"
    end

    private

    def load_json(site, path)
      file = File.join(site.source, path)
      return [] unless File.exist?(file)
      JSON.parse(File.read(file, encoding: 'utf-8'))
    rescue => e
      Jekyll.logger.warn "OfficeGenerator:", "#{path} 로드 실패: #{e.message}"
      []
    end
  end

  class OfficePage < Page
    def initialize(site, o)
      @site = site
      @base = site.source
      @dir  = "office/#{o['slug']}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'office.html')
      self.data.merge!(o)
      self.data['layout']      = 'office'
      self.data['title']       = build_title(o)
      self.data['description'] = build_desc(o)
    end

    private

    def build_title(o)
      loc = [o['doShort'], o['sigungu']].compact.join(' ')
      "#{o['officeName']} #{loc} 위치 전화번호 보유장비"
    end

    def build_desc(o)
      loc = [o['doShort'], o['sigungu']].compact.join(' ')
      equip_names = (o['equipment'] || []).map { |e| e['label'] }.first(5).join('·')
      "#{loc} #{o['officeName']}의 위치, 전화번호, 보유 농기계(#{equip_names})를 확인하세요."[0, 155]
    end
  end
end
