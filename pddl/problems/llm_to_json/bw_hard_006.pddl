(define (problem bw_hard_006)
  (:domain blocks-world)

  (:objects
    a b c d e - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on_table e)
    (on d e)
    (clear c)
    (clear a)
    (clear b)
    (handempty)
  )

  (:goal
    (and
      (on a c)
      (on b a)
    )
  )
)
